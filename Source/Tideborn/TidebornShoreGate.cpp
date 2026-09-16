#include "TidebornShoreGate.h"
#include "TidebornCreature.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"

ATidebornShoreGate::ATidebornShoreGate()
{
	PrimaryActorTick.bCanEverTick = true;

	BlockVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("BlockVolume"));
	SetRootComponent(BlockVolume);
	BlockVolume->SetBoxExtent(FVector(80.f, 200.f, 160.f));
	BlockVolume->SetCollisionProfileName(TEXT("BlockAll"));

	GateMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("GateMesh"));
	GateMesh->SetupAttachment(RootComponent);
	GateMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeMesh.Succeeded())
	{
		GateMesh->SetStaticMesh(CubeMesh.Object);
		GateMesh->SetRelativeScale3D(FVector(0.4f, 4.0f, 3.2f));
	}
}

void ATidebornShoreGate::BeginPlay()
{
	Super::BeginPlay();
	SetGateOpen(false);
	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial")))
	{
		if (UMaterialInstanceDynamic* Dyn = UMaterialInstanceDynamic::Create(Base, this))
		{
			Dyn->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.35f, 0.4f, 0.55f));
			GateMesh->SetMaterial(0, Dyn);
		}
	}
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
		SetActorHiddenInGame(false);
		GateMesh->SetVisibility(false);
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(95001, 10.f, FColor::Cyan, TEXT("Shore Gate OPEN — tamed companion nearby"));
		}
	}
	else
	{
		BlockVolume->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		BlockVolume->SetCollisionProfileName(TEXT("BlockAll"));
		GateMesh->SetVisibility(true);
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(95001, 6.f, FColor::Orange, TEXT("Shore Gate CLOSED — bring a tamed Kelp-back"));
		}
	}
}

void ATidebornShoreGate::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	SetGateOpen(HasTamedCompanionNearPlayer());
}
