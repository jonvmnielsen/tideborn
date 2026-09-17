#include "TidebornLandmarkBeacon.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ATidebornLandmarkBeacon::ATidebornLandmarkBeacon()
{
	PrimaryActorTick.bCanEverTick = false;

	PostMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PostMesh"));
	SetRootComponent(PostMesh);
	PostMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> PostSM(TEXT("/Game/Tideborn/Meshes/SM_PathPost.SM_PathPost"));
	if (PostSM.Succeeded())
	{
		PostMesh->SetStaticMesh(PostSM.Object);
		PostMesh->SetRelativeScale3D(FVector(1.f));
	}

	WarmLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("WarmLight"));
	WarmLight->SetupAttachment(RootComponent);
	WarmLight->SetRelativeLocation(FVector(0.f, 0.f, 220.f));
	WarmLight->SetLightColor(FLinearColor(1.f, 0.72f, 0.35f));
	WarmLight->SetIntensity(3500.f);
	WarmLight->SetAttenuationRadius(1400.f);
	WarmLight->SetCastShadows(false);
}

void ATidebornLandmarkBeacon::BeginPlay()
{
	Super::BeginPlay();
}
