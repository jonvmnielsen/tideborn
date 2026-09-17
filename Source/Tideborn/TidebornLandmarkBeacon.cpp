#include "TidebornLandmarkBeacon.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"
#include "TidebornNameTagComponent.h"

ATidebornLandmarkBeacon::ATidebornLandmarkBeacon()
{
	PrimaryActorTick.bCanEverTick = false;

	PostMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PostMesh"));
	SetRootComponent(PostMesh);
	PostMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CylinderMesh.Succeeded())
	{
		PostMesh->SetStaticMesh(CylinderMesh.Object);
		PostMesh->SetRelativeScale3D(FVector(0.22f, 0.22f, 3.8f));
	}
	else if (CubeMesh.Succeeded())
	{
		PostMesh->SetStaticMesh(CubeMesh.Object);
		PostMesh->SetRelativeScale3D(FVector(0.18f, 0.18f, 3.8f));
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

	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial")))
	{
		if (UMaterialInstanceDynamic* Dyn = UMaterialInstanceDynamic::Create(Base, this))
		{
			Dyn->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.55f, 0.35f, 0.15f));
			PostMesh->SetMaterial(0, Dyn);
		}
	}

	if (UTidebornNameTagComponent* Tag = NewObject<UTidebornNameTagComponent>(this, TEXT("NameTag")))
	{
		Tag->HeightOffset = 260.f;
		Tag->TitleSize = 48.f;
		Tag->TitleColor = FColor(255, 200, 120);
		Tag->Title = TEXT("Path Post");
		Tag->Subtitle = TEXT("Landmark — follow warm lights to Shore Gate");
		AddInstanceComponent(Tag);
		Tag->RegisterComponent();
	}
}
