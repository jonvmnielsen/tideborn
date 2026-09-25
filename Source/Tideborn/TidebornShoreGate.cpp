#include "TidebornShoreGate.h"
#include "TidebornCreature.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
#include "Engine/Engine.h"

ATidebornShoreGate::ATidebornShoreGate()
{
	PrimaryActorTick.bCanEverTick = true;

	BlockVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("BlockVolume"));
	SetRootComponent(BlockVolume);
	BlockVolume->SetBoxExtent(FVector(220.f, 80.f, 220.f));
	BlockVolume->SetCollisionProfileName(TEXT("BlockAll"));

	GateMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("GateMesh"));
	GateMesh->SetupAttachment(RootComponent);
	GateMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> GateSM(TEXT("/Game/Tideborn/Meshes/SM_ShoreGate.SM_ShoreGate"));
	if (GateSM.Succeeded())
	{
		GateMesh->SetStaticMesh(GateSM.Object);
		GateMesh->SetRelativeLocation(FVector(0.f, 0.f, -220.f));
	}

	VistaLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("VistaLight"));
	VistaLight->SetupAttachment(RootComponent);
	VistaLight->SetRelativeLocation(FVector(0.f, 0.f, 320.f));
	VistaLight->SetLightColor(FLinearColor(1.f, 0.72f, 0.42f)); // warm wood lantern (was teal)
	VistaLight->SetIntensity(1800.f);
	VistaLight->SetAttenuationRadius(2200.f);
	VistaLight->SetCastShadows(false);
}

void ATidebornShoreGate::BeginPlay()
{
	Super::BeginPlay();
	SetGateOpen(false);
}

bool ATidebornShoreGate::HasTamedCompanionNearPlayer() const
{
	APawn* Player = UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
	if (!Player)
	{
		return false;
	}

	for (TActorIterator<ATidebornCreature> It(GetWorld()); It; ++It)
	{
		ATidebornCreature* C = *It;
		if (!C || !C->bTamed)
		{
			continue;
		}
		if (FVector::Dist(C->GetActorLocation(), Player->GetActorLocation()) <= CompanionCheckRadius)
		{
			return true;
		}
	}
	return false;
}

void ATidebornShoreGate::SetGateOpen(bool bShouldOpen)
{
	if (bOpen == bShouldOpen)
	{
		return;
	}
	bOpen = bShouldOpen;
	if (bOpen)
	{
		BlockVolume->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		GateMesh->SetVisibility(false);
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(95001, 10.f, FColor::Cyan, TEXT("Shore Gate OPEN - tamed companion nearby"));
		}
	}
	else
	{
		BlockVolume->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		BlockVolume->SetCollisionProfileName(TEXT("BlockAll"));
		GateMesh->SetVisibility(true);
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(95001, 6.f, FColor::Orange, TEXT("Shore Gate CLOSED - bring a tamed Kelp-back"));
		}
	}
}

void ATidebornShoreGate::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	SetGateOpen(HasTamedCompanionNearPlayer());
}
